function start(){
    document.getElementById("ticket-add-file").value = null;
    document.getElementById("ticket-add-file").onchange=function() {
        input = document.getElementById('ticket-add-file');
        for (i = 0; i <= input.files.length-1; i++) {
            file = input.files[i];
            file_size=file.size;
            if (file_size > 10000000) {
                document.getElementById("size-error-label").style.display = 'block';
                return
            }
            else {
                document.getElementById("size-error-label").style.display = 'none';
            }
        }
    };

    document.getElementById("ticket-send-message").onkeydown=function(e) {
        if (e.keyCode == 13) {
            e.preventDefault();
        }
    };

    document.getElementById("submit-ticket").onclick=function() {
        if (document.getElementById("size-error-label").style.display === 'block') {
            return;
        }
        else {
            document.getElementById("ticket_send_form").submit();
        }
    };
};
document.onload=start();