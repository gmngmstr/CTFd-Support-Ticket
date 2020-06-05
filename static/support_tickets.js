function load() {
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