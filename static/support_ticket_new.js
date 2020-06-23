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

    function bodyAppend(tagName, innerHTML) {
        var elm;

        elm = document.createElement(tagName);
        elm.innerHTML = innerHTML;
        document.body.appendChild(elm);
    }

    document.getElementById("create-ticket-select-category").value = "--";
    document.getElementById("create-ticket-select-category").onchange=function() {
        if (this.value === "--") {
            document.getElementById("ticket-create-form").style.display = 'none';
            document.getElementById("submit-ticket").style.display = 'none';
            return;
        }
        resetChallengeList(this.value);
        document.getElementById("ticket-create-form").style.display = 'block';
        document.getElementById("submit-ticket").style.display = 'block';
        document.getElementById("create-ticket-category").value = this.value;
    };

    document.getElementById("create-ticket-select-challenge").onchange=function() {
        if (this.value === "--") {
            document.getElementById("create-ticket-select-challenge-error").style.display = 'block';
            return;
        }
        document.getElementById("create-ticket-select-challenge-error").style.display = 'none';
    };

    document.getElementById("create-ticket-name-issue").value = "";
    document.getElementById("create-ticket-name-issue").onchange=function() {
        if (this.value === "") {
            document.getElementById("create-ticket-name-issue-error").style.display = 'block';
            return;
        }
        document.getElementById("create-ticket-name-issue-error").style.display = 'none';
    };

    document.getElementById("create-ticket-add-file").value = null;
    document.getElementById("create-ticket-add-file").onchange=function() {
        input = document.getElementById('create-ticket-add-file');
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

    document.getElementById("create-ticket-name-issue").onkeydown=function(e) {
        if (e.keyCode == 13) {
            e.preventDefault();
        }
    };

    document.getElementById("submit-ticket").onclick=function() {
        if (document.getElementById("create-ticket-select-challenge").value === "--") {
            document.getElementById("create-ticket-select-challenge-error").style.display = 'block';
            return;
        }
        else if (document.getElementById("create-ticket-name-issue").value === "") {
            document.getElementById("create-ticket-name-issue-error").style.display = 'block';
            return;
        }
        else if (document.getElementById("size-error-label").style.display === 'block') {
            return;
        }
        else {
            document.getElementById("ticket-create-form").submit();
        }
    };
};
document.onload=start();