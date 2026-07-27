import { Compass, Heart, MessageCircle, Radio, User, Users, Zap } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/discover", label: "Discover", icon: Compass },
  { to: "/matches", label: "Matches", icon: Heart },
  { to: "/messages", label: "Messages", icon: MessageCircle },
  { to: "/communities", label: "Communities", icon: Users },
  { to: "/airtime", label: "Airtime", icon: Zap },
  { to: "/profile", label: "Profile", icon: User },
];

function NavItemDesktop({ to, label, icon: Icon }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
          isActive ? "bg-night-700 text-signal" : "text-mist-500 hover:bg-night-800 hover:text-mist-100"
        }`
      }
    >
      <Icon size={18} />
      {label}
    </NavLink>
  );
}

function NavItemMobile({ to, label, icon: Icon }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex flex-1 flex-col items-center gap-1 py-2 text-[11px] font-medium ${
          isActive ? "text-signal" : "text-mist-500"
        }`
      }
    >
      <Icon size={20} />
      {label}
    </NavLink>
  );
}

export default function AppShell() {
  return (
    <div className="min-h-screen bg-night-900 text-mist-100">
      <div className="mx-auto flex max-w-6xl">
        {/* Desktop sidebar */}
        <aside className="sticky top-0 hidden h-screen w-56 flex-col justify-between border-r border-night-700 px-4 py-6 md:flex">
          <div>
            <div className="mb-8 flex items-center gap-2 px-2">
              <span className="signal-bars text-signal">
                <span></span><span></span><span></span><span></span>
              </span>
              <span className="font-display text-lg font-bold">ConnectLite</span>
            </div>
            <nav className="flex flex-col gap-1">
              {NAV_ITEMS.map((item) => (
                <NavItemDesktop key={item.to} {...item} />
              ))}
            </nav>
          </div>
          <NavLink
            to="/notifications"
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium ${
                isActive ? "bg-night-700 text-signal" : "text-mist-500 hover:bg-night-800 hover:text-mist-100"
              }`
            }
          >
            <Radio size={18} />
            Notifications
          </NavLink>
        </aside>

        {/* Main content */}
        <main className="min-h-screen flex-1 pb-20 md:pb-0">
          <Outlet />
        </main>
      </div>

      {/* Mobile bottom nav */}
      <nav className="fixed inset-x-0 bottom-0 z-10 flex border-t border-night-700 bg-night-950/95 backdrop-blur md:hidden">
        {NAV_ITEMS.slice(0, 5).map((item) => (
          <NavItemMobile key={item.to} {...item} />
        ))}
      </nav>
    </div>
  );
}
