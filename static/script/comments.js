function collapseComment(event) {
	var element = event.target;
	for (var i = 0; i < 6; i++) {
		element = element.parentNode;
	}
	if (element.classList.contains("comment-hidden")) {
		// Show
		event.target.innerHTML = "&ndash;";
		element.classList.remove("comment-hidden");
	} else {
		// Hide
		event.target.innerHTML = "+";
		element.classList.add("comment-hidden");
	}
}
