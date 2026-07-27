import { useEffect, useState } from "react";
import { Send } from "lucide-react";
import { useLocation } from "react-router-dom";
import { MessagingAPI } from "../api/resources";
import EmptyState from "../components/EmptyState.jsx";
import LoadingState from "../components/LoadingState.jsx";

export default function Messages() {
  const location = useLocation();
  const [conversations, setConversations] = useState(null);
  const [activeId, setActiveId] = useState(null);
  const [pendingUserId, setPendingUserId] = useState(location.state?.userId || null);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");

  function loadConversations() {
    MessagingAPI.conversations().then(setConversations).catch(() => setConversations([]));
  }

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    if (activeId) {
      MessagingAPI.messages(activeId).then(setMessages);
    }
  }, [activeId]);

  const activeConversation = conversations?.find((c) => c.id === activeId);

  async function handleSend(e) {
    e.preventDefault();
    if (!draft.trim()) return;

    if (pendingUserId) {
      await MessagingAPI.send(pendingUserId, draft);
      setPendingUserId(null);
      setDraft("");
      loadConversations();
      return;
    }

    if (!activeConversation) return;
    await MessagingAPI.send(activeConversation.other_participant.id, draft);
    setDraft("");
    MessagingAPI.messages(activeId).then(setMessages);
  }

  return (
    <div className="mx-auto flex h-[calc(100vh-1px)] max-w-4xl md:h-screen">
      {/* Conversation list */}
      <aside className={`${activeId || pendingUserId ? "hidden md:flex" : "flex"} w-full flex-col border-r border-night-700 md:w-72`}>
        <h1 className="p-4 font-display text-xl font-bold">Messages</h1>
        {!conversations && <LoadingState label="Loading conversations" />}
        {conversations?.length === 0 && !pendingUserId && (
          <div className="px-4">
            <EmptyState title="No conversations yet" body="Match with someone to start chatting." />
          </div>
        )}
        <div className="flex-1 overflow-y-auto">
          {conversations?.map((c) => (
            <button
              key={c.id}
              onClick={() => {
                setActiveId(c.id);
                setPendingUserId(null);
              }}
              className={`flex w-full items-center gap-3 px-4 py-3 text-left hover:bg-night-800 ${
                activeId === c.id ? "bg-night-800" : ""
              }`}
            >
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-night-600 font-display font-semibold">
                {c.other_participant.full_name?.[0]}
              </div>
              <div className="min-w-0">
                <p className="truncate font-medium">{c.other_participant.full_name}</p>
                <p className="truncate text-xs text-mist-500">
                  {c.last_message ? c.last_message.content : "Say hello 👋"}
                </p>
              </div>
            </button>
          ))}
        </div>
      </aside>

      {/* Thread */}
      <section className={`${activeId || pendingUserId ? "flex" : "hidden md:flex"} flex-1 flex-col`}>
        {!activeId && !pendingUserId && (
          <div className="flex flex-1 items-center justify-center text-mist-500">Select a conversation</div>
        )}

        {(activeId || pendingUserId) && (
          <>
            <div className="flex items-center gap-2 border-b border-night-700 p-4">
              <button className="md:hidden" onClick={() => { setActiveId(null); setPendingUserId(null); }}>
                ←
              </button>
              <p className="font-medium">{activeConversation?.other_participant.full_name || "New message"}</p>
            </div>
            <div className="flex-1 space-y-2 overflow-y-auto p-4">
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={`max-w-[75%] rounded-2xl px-3 py-2 text-sm ${
                    m.channel === "sms" ? "border border-dashed border-signal/50" : ""
                  } bg-night-700`}
                >
                  {m.content}
                  {m.channel === "sms" && <span className="ml-2 text-[10px] uppercase text-signal">via SMS</span>}
                </div>
              ))}
              {messages.length === 0 && pendingUserId && (
                <p className="text-sm text-mist-500">Send your first message below.</p>
              )}
            </div>
            <form onSubmit={handleSend} className="flex gap-2 border-t border-night-700 p-3">
              <input
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder="Type a message…"
                className="flex-1 rounded-lg bg-night-800 px-3 py-2 text-sm outline-none"
              />
              <button type="submit" className="rounded-lg bg-signal p-2 text-night-950">
                <Send size={18} />
              </button>
            </form>
          </>
        )}
      </section>
    </div>
  );
}
