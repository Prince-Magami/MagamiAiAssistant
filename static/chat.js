document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");
    const chatWindow = document.getElementById("chat-window");

    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const userText = chatInput.value.trim();
        if (!userText) return;

        // Append user's message
        const userBubble = document.createElement("div");
        userBubble.className = "chat-bubble user-msg";
        userBubble.textContent = userText;
        chatWindow.appendChild(userBubble);
        chatWindow.scrollTop = chatWindow.scrollHeight;

        chatInput.value = "";

        const mode = document.getElementById("mode").value;
        const lang = document.getElementById("lang").value;

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: userText, mode: mode, lang: lang })
            });

            const data = await response.json();

            // Append AI's reply
            const aiBubble = document.createElement("div");
            aiBubble.className = "chat-bubble ai-msg";
            aiBubble.textContent = data.reply;
            chatWindow.appendChild(aiBubble);
            chatWindow.scrollTop = chatWindow.scrollHeight;

        } catch (err) {
            console.error("Chat error:", err);
        }
    });
});
