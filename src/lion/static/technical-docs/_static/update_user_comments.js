var imported = document.createElement('script');
imported.src = 'https://code.jquery.com/jquery-3.6.3.min.js';
document.head.appendChild(imported);

function update_comments(id, filePath) {
    let comnt = document.getElementById(id).value;

    $.post("/update_comments", 
        {request_data: JSON.stringify({
            comment: comnt, 
            sec_id: id,
            filePath: filePath
        })}, 
        function(response) {
        if (response.code === 400) {
            alert(response.message);
            return;
        }
    });
};