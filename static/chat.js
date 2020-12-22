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


var chat = setInterval(function(){ get_chat() }, 1000);

function get_chat() {

    // Use js getAttribute() to get group_id from the html page
    let message_div =  document.getElementById("messages");
    let group_id = message_div.getAttribute("data-chat-id");
    // Connect to the url
    const url = '/chatget/' + group_id
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    // Listen to url and run the function when status changed  (AJAX - onreadystatechange)
    xhr.onreadystatechange=function()
    {
        // (AJAX - onreadystatechange)
        if (xhr.readyState==4 && xhr.status==200)
        {
            message_div.innerHTML=xhr.responseText;
        }
    }
    xhr.send()

    // onreadystatechange
    // document.getElementById("user").innerHTML = ?;
    // document.getElementById("friends").innerHTML = ?;
}
