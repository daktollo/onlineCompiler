import { useBlockDisplaysStore } from "../stores/blockDisplays";

let eventSource = null;
let currentUserId = null;
let reconnectTimer = null;
let retryDelayMs = 1000;

export function startBlockEvents(userId) {
  if (!userId) return;
  if (currentUserId === userId && eventSource) return;

  stopBlockEvents();

  currentUserId = userId;
  const url = `http://localhost:5001/events?user_id=${encodeURIComponent(userId)}`;
  const store = useBlockDisplaysStore();

  const connect = () => {
    console.log("[SSE] connecting to", url);
    eventSource = new EventSource(url);

    eventSource.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        console.log("[SSE] message:", data);
        if (data.type === "display_create") {
          store.onDisplayCreate(data);
        } else if (data.type === "block_update") {
          store.onBlockUpdate(data);
        }
      } catch (_) {
        // ignore parse errors
      }
    };

    eventSource.onerror = (err) => {
      console.warn("[SSE] error, reconnecting...", err);
      stopBlockEvents();
      scheduleReconnect();
    };

    eventSource.onopen = () => {
      console.log("[SSE] connected");
    };
  };

  const scheduleReconnect = () => {
    if (reconnectTimer) return;
    const delay = retryDelayMs;
    console.log(`[SSE] reconnecting in ${delay}ms`);
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null;
      retryDelayMs = Math.min(retryDelayMs * 2, 15000);
      connect();
    }, retryDelayMs);
  };

  connect();
}

export function stopBlockEvents() {
  if (eventSource) {
    eventSource.close();
    eventSource = null;
  }
  currentUserId = null;
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  // reset backoff for next start
  retryDelayMs = 1000;
}
