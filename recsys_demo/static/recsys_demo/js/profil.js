$(document).ready(function () {
    $("#submit_rating").on('click', function () {

    var movie_title = document.getElementById("m_title").innerHTML;
    console.log(movie_title)

    $.ajax({
        method: 'POST',
        url: '/movie_rec/profil',
        data: {action: 'first_call', 'movie_title': movie_title},
        success: function (data) {
            console.log("It worked")
            console.log(data)
            $("#user_rating").rating('create');
            var input_rating = $("#user_rating").rating('create').val()
            console.log(input_rating)
            var movie_id = data
            console.log(movie_id)
            var data_dict = {};
            data_dict.movie_id = movie_id;
            data_dict.movie_rating = input_rating;

            $.ajax({
                method: 'POST',
                url: '/movie_rec/profil',
                data: {action: 'second_call', 'data_dict': data_dict},
                success: function (data) {
                     //this gets called when server returns an OK response
                    },
                error: function (data) {
                     alert("it didnt work");
                    }
                });
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
