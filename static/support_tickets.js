function load() {

    for (var id in ticket_list["Pending"]) {
        let ticket = document.createElement('div');
        ticket.setAttribute('class', "col-md-3 d-inline-block");
        let ticket_button = document.createElement('button');
        ticket_button.setAttribute('class', "btn btn-dark challenge-button w-100 text-truncate pt-3 pb-3 mb-2");
        ticket_button.setAttribute('name', "ticket");
        ticket_button.setAttribute('type', "submit");
        ticket_button.value = id;
        let ticket_button_p = document.createElement('p');
        ticket_button_p.innerHTML = "Category: " + ticket_list["Pending"][id]["category"]
        let ticket_button_span = document.createElement('span');
        ticket_button_span.innerHTML = "Challenge: " + ticket_list["Pending"][id]["name"]
        if (access == "Admin") {
            ticket_button_user = document.createElement('p');
            ticket_button_user.innerHTML = "Creator: " + ticket_list["Pending"][id]["user"]
            ticket_button.append(ticket_button_user)
        }
        ticket_button.append(ticket_button_p)
        ticket_button.append(ticket_button_span)
        ticket.append(ticket_button);
        document.getElementById("Pending-tickets").append(ticket);
    }
    for (var id in ticket_list["Open"]) {
        let ticket = document.createElement('div');
        ticket.setAttribute('class', "col-md-3 d-inline-block");
        let ticket_button = document.createElement('button');
        ticket_button.setAttribute('class', "btn btn-dark challenge-button w-100 text-truncate pt-3 pb-3 mb-2");
        ticket_button.setAttribute('name', "ticket");
        ticket_button.setAttribute('type', "submit");
        ticket_button.value = id;
        let ticket_button_p = document.createElement('p');
        ticket_button_p.innerHTML = "Category: " + ticket_list["Open"][id]["category"]
        let ticket_button_span = document.createElement('span');
        ticket_button_span.innerHTML = "Challenge: " + ticket_list["Open"][id]["name"]
        if (access == "Admin") {
            ticket_button_user = document.createElement('p');
            ticket_button_user.innerHTML = "Creator: " + ticket_list["Open"][id]["user"]
            ticket_button.append(ticket_button_user)
        }
        ticket_button.append(ticket_button_p)
        ticket_button.append(ticket_button_span)
        ticket.append(ticket_button);
        document.getElementById("Open-tickets").append(ticket);
    }
    for (var id in ticket_list["Closed"]) {
        let ticket = document.createElement('div');
        ticket.setAttribute('class', "col-md-3 d-inline-block");
        let ticket_button = document.createElement('button');
        ticket_button.setAttribute('class', "btn btn-dark challenge-button w-100 text-truncate pt-3 pb-3 mb-2");
        ticket_button.setAttribute('name', "ticket");
        ticket_button.setAttribute('type', "submit");
        ticket_button.value = id;
        let ticket_button_p = document.createElement('p');
        ticket_button_p.innerHTML = "Category: " + ticket_list["Closed"][id]["category"]
        let ticket_button_span = document.createElement('span');
        ticket_button_span.innerHTML = "Challenge: " + ticket_list["Closed"][id]["name"]
        if (access == "Admin") {
            ticket_button_user = document.createElement('p');
            ticket_button_user.innerHTML = "Creator: " + ticket_list["Closed"][id]["user"]
            ticket_button.append(ticket_button_user)
        }
        ticket_button.append(ticket_button_p)
        ticket_button.append(ticket_button_span)
        ticket.append(ticket_button);
        document.getElementById("Closed-tickets").append(ticket);
    }
    if (document.getElementById("Pending-tickets").childNodes.length >= 2) {
        document.getElementById("Pending-board").style.display = 'block';
    }
    if (document.getElementById("Open-tickets").childNodes.length >= 2) {
        document.getElementById("Open-board").style.display = 'block';
    }
    if (document.getElementById("Closed-tickets").childNodes.length >= 2) {
        document.getElementById("Closed-board").style.display = 'block';
    }
};
document.onload=load();