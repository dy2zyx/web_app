$(document).ready(function () {
    var feedback_dict = {};
	$('.rating').on('rating.change', function(event, value) {
			ratingValue = value
            e_id = this.id
            feedback_dict[e_id] = ratingValue
//            console.log(feedback_dict)
//            alert("ssss")
	});
   $("#feedback_exp_top1_2").on('click', function () {
//        alert("Not working")
        console.log("ajax")
        console.log(feedback_dict)
        $.ajax({
            method: 'POST',
            url: window.location.href,
            data: {'feedback_top1_2': JSON.stringify(feedback_dict)},
            success: function (data) {
                 //this gets called when server returns an OK response
        //            alert(data)
                },
            error: function (data) {
//                 alert("it didnt work");
//                 console.log(data)
                }
        });
    });
});

