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

    // Get the user_id,group_id,friend_name from chatroom.html
    let mainDiv = document.getElementById("main_div");
    let user_id = mainDiv.getAttribute("data-user-id");
    let group_id = mainDiv.getAttribute("data-group-id");
    let friend_name = mainDiv.getAttribute("data-friend-name");

    // Create a boolean to check if the scroll already at the bottom or not
    let lock_distance = 5;
    let element = document.getElementById("messages");
    // console.log(element.scrollHeight, element.clientHeight, element.scrollTop, element.scrollHeight - element.clientHeight, element.scrollHeight - element.scrollTop);
    // This is slightly wrong when it shouldn't be: scrollTop == scrollHeight - clientHeight
    let scroll_check = Math.abs(element.scrollTop - (element.scrollHeight - element.clientHeight)) < lock_distance;

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
            document.getElementById("messages").innerHTML = "";

            // Add messages history to the div
            let n = result.length;
            for (i = 0; i < n; i++) {
                var id = result[i]["user_id"];

                // Make a each new div to keep message 
                let messageDiv = document.getElementById("messages");
                let newDiv;
                let newContent = document.createElement("span");

                // https://github.com/joypixels/emoji-toolkit/blob/master/examples/JAVASCRIPT.md
                var output = joypixels.toImage(result[i]["content"])


                if (id == user_id) {
                    newDiv = document.createElement("div");
                    newContent.innerHTML = output
                    // newContent = document.createTextNode(`${result[i]["content"]}`);

                    let att = document.createAttribute("class");                     // Create a "class" attribute
                    att.value = "fst-italic p-3 border-bottom text-success bg-light";  // Set the value of the class attribute
                    newDiv.setAttributeNode(att);

                    newDiv.appendChild(newContent);
                } else {
                    newDiv = document.createElement("div");
                    newContent.innerHTML = output + ` (${friend_name})`
                    // newContent = document.createTextNode(`${result[i]["content"]} (${friend_name})`);

                    let att = document.createAttribute("class");                                // Create a "class" attribute
                    att.value = "text-end p-3 border-bottom text-dark bg-light";    // Set the value of the class attribute
                    newDiv.setAttributeNode(att);

                    newDiv.appendChild(newContent);
                }
                messageDiv.appendChild(newDiv);
            }
                // search---scroll stay end
                if (scroll_check){
                    element.scrollTop = element.scrollHeight;    
                }
        }
    }
    xhr.send()
}
