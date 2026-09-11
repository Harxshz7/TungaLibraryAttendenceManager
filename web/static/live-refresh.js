(function() {
    const tbody = document.getElementById("live-sessions-body");
    const badge = document.getElementById("live-indicator");
    const statusText = document.getElementById("live-status-text");

    let eventSource = null;
    let reconnectTimeout = null;

    function escapeHtml(text) {
        if (text === null || text === undefined) return "";
        return String(text)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function renderSessions(sessions) {
        if (!tbody) return;
        if (!sessions || sessions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6">No active sessions today.</td></tr>';
            return;
        }

        const html = sessions.map(s => {
            const endDisplay = s.end_at ? escapeHtml(s.end_at) : '<span class="status-active">Active</span>';
            const duration = s.duration_sec !== null && s.duration_sec !== undefined ? s.duration_sec : "";
            return `<tr>
                <td>${escapeHtml(s.student_id)}</td>
                <td>${escapeHtml(s.name || "")}</td>
                <td>${escapeHtml(s.class || "")}</td>
                <td>${escapeHtml(s.start_at || "")}</td>
                <td>${endDisplay}</td>
                <td>${duration}</td>
            </tr>`;
        }).join("");

        tbody.innerHTML = html;
    }

    function connect() {
        if (eventSource) {
            try {
                eventSource.close();
            } catch (e) {}
        }

        eventSource = new EventSource("/events/live-sessions");

        eventSource.onopen = function() {
            if (badge) badge.classList.remove("offline");
            if (statusText) statusText.textContent = "Live";
        };

        eventSource.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                renderSessions(data);
            } catch (err) {
                console.error("Failed to parse SSE live session data:", err);
            }
        };

        eventSource.onerror = function() {
            if (badge) badge.classList.add("offline");
            if (statusText) statusText.textContent = "Reconnecting...";
            eventSource.close();

            clearTimeout(reconnectTimeout);
            reconnectTimeout = setTimeout(connect, 3000);
        };
    }

    // Initialize SSE connection on page load
    connect();
})();
