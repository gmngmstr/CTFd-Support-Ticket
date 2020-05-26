function start(){
    function addChallenge(category_name, show_error=true) {
        var challenges = challenge_categories[category_name];

        let challenge_list = document.createElement('option');
        challenge_list.innerHTML = "--";
        document.getElementById("create-ticket-select-challenge").append(challenge_list);

        for (var key in challenges) {
            let challenge_list = document.createElement('option');
            value = challenges[key];
            challenge_list.attr = value, key;
            challenge_list.innerHTML = value;
            document.getElementById("create-ticket-select-challenge").append(challenge_list);
        };
    }

    function resetChallengeList(category_name) {
        var select = document.getElementById("create-ticket-select-challenge");
        var length = select.options.length;
        for (i = length-1; i >= 0; i--) {
            select.options[i] = null;
        }
        addChallenge(category_name, show_error=false);
    }


    function showFileSize() {
        var input, file;

        // (Can't use `typeof FileReader === "function"` because apparently
        // it comes back as "object" on some browsers. So just see if it's there
        // at all.)
        if (!window.FileReader) {
            bodyAppend("p", "The file API isn't supported on this browser yet.");
            return;
        }

        input = document.getElementById('create-ticket-add-file');
        if (!input) {
            bodyAppend("p", "Um, couldn't find the create-ticket-add-file element.");
        }
        else if (!input.files) {
            bodyAppend("p", "This browser doesn't seem to support the `files` property of file inputs.");
        }
        else if (!input.files[0]) {
            bodyAppend("p", "Please select a file before clicking 'Load'");
        }
        else {
            file = input.files[0];
            return file.size;
        }
    }

    function bodyAppend(tagName, innerHTML) {
        var elm;

        elm = document.createElement(tagName);
        elm.innerHTML = innerHTML;
        document.body.appendChild(elm);
    }


    document.getElementById("create-ticket-select-category").value = "--";
    document.getElementById("create-ticket-select-category").onchange=function() {
        if (this.value === "--") {
            document.getElementById("ticket_create_form").style.display = 'none';
            return;
        }
        resetChallengeList(this.value);
        document.getElementById("ticket_create_form").style.display = 'block';
        document.getElementById("create-ticket-category").value = this.value;
    };

    document.getElementById("create-ticket-name-issue").value = "";

    document.getElementById("create-ticket-add-file").value = "";
    document.getElementById("create-ticket-add-file").onchange=function() {
        file_size=showFileSize();
        if (file_size > 10000000) {
            document.getElementById("size-error-label").style.display = 'block';
        }
        else {
            document.getElementById("size-error-label").style.display = 'none';
        }
    };
};
document.onload=start();