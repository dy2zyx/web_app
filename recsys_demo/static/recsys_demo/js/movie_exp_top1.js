$(document).ready(function () {
    var feedback_dict = {};
	$('.rating').on('rating.change', function(event, value) {
			ratingValue = value
            e_id = this.id
            feedback_dict[e_id] = ratingValue
//            console.log(Object.keys(feedback_dict).length)
	});
   $("#feedback_exp_top1").on('click', function () {
        if (Object.keys(feedback_dict).length !== 5) {
             alert("Veuillez vérifier que vous avez rempli (noté) tous les champs. Nous vous rappelons que la note de 0 n'est pas autorisée et que la note la plus basse est de 1 étoile.")
        } else {
                var x = document.getElementById("feedback_exp_top1_done");
                if (x.style.display === "none") {
                    x.style.display = "block";
                   } else {
                    x.style.display = "none";
                   }
                $.ajax({
                method: 'POST',
                url: window.location.href,
                data: {'feedback_top1': JSON.stringify(feedback_dict)},
                success: function (data) {
                     //this gets called when server returns an OK response
            //            alert(data)
                    },
                error: function (data) {
    //                 alert("it didnt work");
    //                 console.log(data)
                    }
            });
        }
    });
});

//function myFunc(){
//  var x = document.getElementById("feedback_exp_top1_done");
//  if (x.style.display === "none") {
//    x.style.display = "block";
//  } else {
//    x.style.display = "none";
//  }
//}


