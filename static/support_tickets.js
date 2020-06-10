function load() {
    if (document.getElementById("Submitted-tickets").childNodes.length >= 2) {
        document.getElementById("Submitted-board").style.display = 'block';
    }
    if (document.getElementById("In-Progress-tickets").childNodes.length >= 2) {
        document.getElementById("In-Progress-board").style.display = 'block';
    }
    if (document.getElementById("Closed-tickets").childNodes.length >= 2) {
        document.getElementById("Closed-board").style.display = 'block';
    }
};
document.onload=load();