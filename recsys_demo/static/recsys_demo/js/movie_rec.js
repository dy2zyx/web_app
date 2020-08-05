$(document).ready(function () {
    $("#submit_rating").on('click', function () {
        $("#user_rating").rating('create');
//        alert($("#user_rating").rating('create').val());
    var input_rating = $("#user_rating").rating('create').val()
    console.log(movie_id)
    var data_dict = {};
    data_dict.movie_id = movie_id;
    data_dict.movie_rating = input_rating;

    $.ajax({
        method: 'POST',
        url: '/movie_rec',
        data: {'data_dict': data_dict},
        success: function (data) {
             //this gets called when server returns an OK response
//             alert("it worked!");
//            alert(data)
            },
        error: function (data) {
             alert("it didnt work");
            }
        });
    });
});


$('#rating_form').submit(function(e){
    e.preventDefault();
    url = $(this).attr('action');
    data = $(this).serialize();
    $.post(url, data, function(response){
    });
});
