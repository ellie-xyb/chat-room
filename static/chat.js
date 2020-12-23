function get_content(group_id) {
    // Get the value of input
    const content = document.getElementById('content').value;
    const url = '/chatsave/' + group_id
    var xhr = new XMLHttpRequest();
    xhr.open("POST", url, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.send(JSON.stringify({
        value: content
    }));
    // at once sent the value, clear the input
    document.getElementById('content').value = "";
    document.getElementById('content').focus();
}


var chat = setInterval(function () { get_chat() }, 1000);

function get_chat() {

    // Use js getAttribute() to get group_id from the html page

    // Get the user_id from chatroom.html
    let user_div = document.getElementById("user_m");
    let user_id = user_div.getAttribute("data-user-id");

    // // Get the group_id from html
    let friend_div = document.getElementById("friend_m");
    let group_id = friend_div.getAttribute("data-group-id");

    // Create an arry to keep the json response of messages and user_ids
    let result = [];

    // Connect to the url
    const url = '/chatget/' + group_id
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    // Listen to url and run the function when status changed  (AJAX - onreadystatechange)
    xhr.onreadystatechange = function () {
        // (AJAX - onreadystatechange)
        if (xhr.readyState == 4 && xhr.status == 200) {
            // Get “Data” field from xhr.responseText, get the json response 
            result = JSON.parse(xhr.responseText);

            // clean the div first
            document.getElementById("user_m").innerHTML = "";
            document.getElementById("friend_m").innerHTML = "";

            // Add messages history to the div
            let n = result.length;
            for (i = 0; i < n; i++) {
                var id = result[i]["user_id"];

                // Make a each new div to keep message 
                let newDiv = document.createElement("div");
                let newContent = document.createTextNode(`${result[i]["user_id"]}: ${result[i]["content"]}`);
                newDiv.appendChild(newContent);

                if (id == user_id) {
                    user_div.appendChild(newDiv);
                } else {
                    friend_div.appendChild(newDiv);
                }
            }
        }
    }
    xhr.send()


}
