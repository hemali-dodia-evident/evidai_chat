var sendBtn = document.getElementById("sendBtn");
var queryField = document.getElementById("user-query-input-field");
var chatArea = document.getElementById("conversation-area");
var conversationContent = document.getElementById("conversation-content");
var conversationPlaceholder = document.getElementById("conversation-placeholder");

queryField.addEventListener('input', onUserInputQuery);

function onUserInputQuery() {
    if (queryField.value.trim() == "") {
        sendBtn.style.backgroundColor = "#9995AF80";
    } else {
        sendBtn.style.backgroundColor = "#4C37B8";
    }
}

sendBtn.addEventListener('click', onUserSubmitQuery);

function onUserSubmitQuery() {
    if (queryField.value.trim() !== "") {
        const userQuestion = queryField.value.trim();

        // Ensure conversation area is visible
        conversationContent.classList.remove("d-none");
        conversationPlaceholder.classList.add("d-none");

        // Create a new user question block
        const questionBlock = document.createElement("div");
        questionBlock.className = "list-group-item border-0 d-flex p-0 mb-3";
        questionBlock.innerHTML = `
            <div class="user-icon-in-chat d-flex justify-content-center align-items-center">Y</div>
            <div class="px-2">
                <div class="talker-title">You</div>
                <div class="mt-1">${userQuestion}</div>
                <ul class="message-options mt-1 list-inline">
                    <li class="list-inline-item cursor-pointer">
                        <img src="/static/assets/volume-up.png">
                    </li>
                    <li class="list-inline-item cursor-pointer">
                        <img src="/static/assets/autorenew.png">
                    </li>
                </ul>
            </div>
        `;

        // Append the user's question to the chat area
        chatArea.appendChild(questionBlock);

        const chat_id = 4; // Replace with dynamic session ID
        const token_value = "c9cd38f12859849f9ad3032322e2e950e676e0ced79782acd988cf1fbca31a5c"; // Replace with dynamic token

        // Create an XMLHttpRequest object
        var xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function () {
            if (xhttp.readyState === 4) {
                if (xhttp.status === 200) {
                    const output = JSON.parse(xhttp.responseText);

                    // Create a new bot response block
                    const responseBlock = document.createElement("div");
                    responseBlock.className = "list-group-item border-0 d-flex p-0 mb-3";
                    responseBlock.innerHTML = `
                        <img src="/static/assets/bot-talker.png" class="bot-icon-in-chat">
                        <div class="px-2">
                            <div class="talker-title">EVIDAI</div>
                            <div class="mt-1">${output.data.response || "No response received."}</div>
                            <ul class="message-options mt-1 list-inline">
                                <li class="list-inline-item cursor-pointer">
                                    <img src="/static/assets/volume-up.png">
                                </li>
                                <li class="list-inline-item cursor-pointer">
                                    <img src="/static/assets/content-copy.png">
                                </li>
                                <li class="list-inline-item cursor-pointer">
                                    <img src="/static/assets/autorenew.png">
                                </li>
                                <li class="list-inline-item cursor-pointer">
                                    <img src="/static/assets/thumb-down.png">
                                </li>
                            </ul>
                        </div>
                    `;

                    // Append the bot's response to the chat area
                    chatArea.appendChild(responseBlock);

                    // Ensure the chat area scrolls to the latest message
                    chatArea.scrollTop = chatArea.scrollHeight;
                } else {
                    console.error("Error:", xhttp.statusText);

                    // Handle error response
                    const errorBlock = document.createElement("div");
                    errorBlock.className = "list-group-item border-0 d-flex p-0 mb-3";
                    errorBlock.innerHTML = `
                        <img src="/static/assets/bot-talker.png" class="bot-icon-in-chat">
                        <div class="px-2">
                            <div class="talker-title">EVIDAI</div>
                            <div class="mt-1 text-danger">An error occurred. Please try again later.</div>
                        </div>
                    `;

                    chatArea.appendChild(errorBlock);
                }
            }
        };

        // Open a POST request to the API
        xhttp.open("POST", apiUrl, true); // Use apiUrl passed dynamically from the template
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.setRequestHeader("X-CSRFToken", csrfToken); // Use csrfToken passed dynamically from the template

        // Send the request
        xhttp.send(
            JSON.stringify({
                question: userQuestion,
                chat_session_id: chat_id,
                token: token_value,
            })
        );

        // Clear the input field
        queryField.value = "";
    }
}
