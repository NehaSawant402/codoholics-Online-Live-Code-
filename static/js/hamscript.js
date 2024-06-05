const hambtn = document.querySelector(".ham-btn");
const list = document.querySelector(".nav-list");
hambtn.addEventListener("click", () => {
    if(hambtn.classList.toggle("open")) {
        list.style.height="40vh";
    }
    else {
        list.style.height="0";
    }
});

// const downloadCode = () => {
//     let user_code = editor.getValue();
//     alert(user_code)
// }
const copyToClipboard = () => {
    let id = document.getElementById("roomID").innerText;
    navigator.clipboard.writeText(id);
    document.getElementById("copy-btn").innerHTML = "Copied";
};


const downloadCode = () => {
    // Get the file content and type from the form
    let user_code = editor.getValue();
    // const content = document.getElementById('fileContent').value;
    const fileType = document.getElementById('lang').value;
    alert("download format is " + fileType)
    // Determine the file extension based on the selected type
    let fileExtension = '';
    switch (fileType) {
        case 'python':
            fileExtension = '.py';
            break;
        case 'C':
            fileExtension = '.c';
            break;
        case 'C++':
            fileExtension = '.cpp';
            break;
        case 'java':
            fileExtension = '.java';
            break;
        default:
            fileExtension = '.txt';
    }
    const blob = new Blob([user_code], { type: 'text/plain' });
    const a = document.createElement('a');
    a.download = 'code' + fileExtension;
    a.href = URL.createObjectURL(blob);
    a.click();
    URL.revokeObjectURL(a.href);
}


const Notes = () => {
    // Get the content from the textarea
    const content = document.getElementById('user-notes').value;

    // Create a blob with the content and the appropriate MIME type
    const blob = new Blob([content], { type: 'text/plain' });

    // Create a link element
    const a = document.createElement('a');
    // Set the download attribute with the desired file name and extension
    a.download = 'notes.txt';
    // Create an object URL for the blob
    a.href = URL.createObjectURL(blob);
    // Programmatically click the link to trigger the download
    a.click();
    // Release the object URL
    URL.revokeObjectURL(a.href);
}

/* Show and display the logs, chats, etc */
const chats = () => {
    let chats = document.getElementById("chats").style;
    let logs = document.getElementById("logs").style;
    let videoCall = document.getElementById("video-call").style;
    let notes = document.getElementById("notes").style;

    chats.display = "grid";
    logs.display = "none";
    videoCall.display = "none";
    notes.display = "none";
};

const logs = () => {
    let chats = document.getElementById("chats").style;
    let logs = document.getElementById("logs").style;
    let videoCall = document.getElementById("video-call").style;
    let notes = document.getElementById("notes").style;

    chats.display = "none";
    logs.display = "block";
    videoCall.display = "none";
    notes.display = "none";
};

const notes = () => {
    let chats = document.getElementById("chats").style;
    let logs = document.getElementById("logs").style;
    let videoCall = document.getElementById("video-call").style;
    let notes = document.getElementById("notes").style;

    chats.display = "none";
    logs.display = "none";
    videoCall.display = "none";
    notes.display = "block";
};

const videoCall = () => {
    let chats = document.getElementById("chats").style;
    let logs = document.getElementById("logs").style;
    let videoCall = document.getElementById("video-call").style;
    let notes = document.getElementById("notes").style;

    chats.display = "none";
    logs.display = "none";
    videoCall.display = "block";
    notes.display = "none";
};