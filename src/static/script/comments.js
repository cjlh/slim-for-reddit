function collapseComment(event) {
	var element = event.target;
	// navigate element hierarchy to get comment container 
	for (var i = 0; i < 6; i++) {
		element = element.parentNode;
	}
	if (element.classList.contains("comment-hidden")) {
		// if hidden, show comment
		event.target.innerHTML = "&ndash;";
		element.classList.remove("comment-hidden");
	} else {
		// if not hidden, hide comment
		event.target.innerHTML = "+";
		element.classList.add("comment-hidden");
	}
}
