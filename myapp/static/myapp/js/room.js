var socket = new ReconnectingWebSocket('ws://localhost:8001/ws/room_updates/');
socket.onmessage = function (event) {
	var data = JSON.parse(event.data);
	// dataExample = {message: "update_rooms", data: {code: "H668Q6", usernames: ["Sydnec", "Player1"], message: "join"}}
	if (data.message === 'update_rooms') {
		var roomData = data.data;
		updateRoomList(roomData);
	}

	function updateRoomList(roomData) {
		switch (roomData.message) {
			case 'leave':
				document
					.querySelectorAll('.username-list')
					.forEach(function (element) {
						if (
							roomData.usernames.includes(element.textContent) ===
							false
						) {
							element.remove();
						}
					});
				break;
			case 'join':
				document
					.querySelectorAll('.username-list')
					.forEach(function (element) {
						element.remove();
					});
				roomData.usernames.forEach(function (username) {
					var liElement = document.createElement('li');
					liElement.className = 'username-list';
					liElement.textContent = username;
					var roomUserList = document.querySelector(
						'#room-username-list'
					);
					roomUserList.appendChild(liElement);
				});
				break;
			case 'delete':
				window.location.href = '/';
				break;
			default:
				break;
		}
	}
};
