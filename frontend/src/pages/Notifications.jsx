import { useEffect, useState } from "react";
import { Heart, MessageCircle, Radio, UserPlus, Users, Zap } from "lucide-react";
import { NotificationsAPI } from "../api/resources";
import EmptyState from "../components/EmptyState.jsx";
import LoadingState from "../components/LoadingState.jsx";

const ICONS = {
  match: Heart,
  connection_request: UserPlus,
  message: MessageCircle,
  community: Users,
  airtime: Zap,
  system: Radio,
};

export default function Notifications() {
  const [notifications, setNotifications] = useState(null);

  useEffect(() => {
    NotificationsAPI.list().then(setNotifications).catch(() => setNotifications([]));
  }, []);

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="mb-6 font-display text-2xl font-bold">Notifications</h1>

      {!notifications && <LoadingState label="Loading notifications" />}
      {notifications?.length === 0 && <EmptyState title="You're all caught up" body="New matches, messages, and requests will show up here." />}

      <div className="flex flex-col gap-2">
        {notifications?.map((n) => {
          const Icon = ICONS[n.notification_type] || Radio;
          return (
            <div key={n.id} className={`flex gap-3 rounded-lg border border-night-700 p-3 ${n.is_read ? "bg-night-900" : "bg-night-800"}`}>
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-night-700 text-signal">
                <Icon size={16} />
              </div>
              <div>
                <p className="text-sm font-medium">{n.title}</p>
                {n.body && <p className="text-sm text-mist-500">{n.body}</p>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
