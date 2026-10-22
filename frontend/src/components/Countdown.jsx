import { useEffect, useState } from "react";

// Renders "in 4m 12s" for a naive-UTC timestamp string from the API.
// We append "Z" to tell the browser the string IS UTC (naive strings
// would otherwise be parsed as LOCAL time - a classic bug).
export default function Countdown({ iso }) {
  const [label, setLabel] = useState("...");

  useEffect(() => {
    const target = new Date(iso + "Z").getTime();
    const update = () => {
      const diff = target - Date.now();
      if (diff <= 0) return setLabel("due now");
      const s = Math.floor(diff / 1000);
      const parts = [];
      if (s >= 3600) parts.push(Math.floor(s / 3600) + "h");
      if (s >= 60) parts.push(Math.floor((s % 3600) / 60) + "m");
      parts.push((s % 60) + "s");
      setLabel("in " + parts.join(" "));
    };
    update(); // run immediately, then every second
    const id = setInterval(update, 1000);
    return () => clearInterval(id); // cleanup: never leak intervals
  }, [iso]);

  return <span className="countdown">{label}</span>;
}
