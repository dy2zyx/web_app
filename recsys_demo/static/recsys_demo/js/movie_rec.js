$(document).ready(function () {
    $("#submit_rating").on('click', function () {
//        $("#user_rating").rating('create');
//    var input_rating = $("#user_rating").rating('create').val()
    var input_rating = 5;
//    console.log(movie_id)
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
//             alert("it didnt work");
            }
        });
    });

    $("#submit_rating_0").on('click', function () {
//        $("#user_rating_0").rating('create');
//    var input_rating = $("#user_rating_0").rating('create').val()
    var input_rating = 5;
    var data_dict = {};
    data_dict.movie_id = random_movie_id_dict[0];
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
//             alert("it didnt work");
            }
        });
    });

    $("#submit_rating_1").on('click', function () {
//        $("#user_rating_1").rating('create');
//        alert($("#user_rating").rating('create').val());
//    var input_rating = $("#user_rating_1").rating('create').val()
    var input_rating = 5;
    var data_dict = {};
    data_dict.movie_id = random_movie_id_dict[1];
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
//             alert("it didnt work");
            }
        });
    });

    $("#submit_rating_2").on('click', function () {
//        $("#user_rating_2").rating('create');
//        alert($("#user_rating").rating('create').val());
//    var input_rating = $("#user_rating_2").rating('create').val()
    var data_dict = {};
    var input_rating = 5;
    data_dict.movie_id = random_movie_id_dict[2];
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
//             alert("it didnt work");
            }
        });
    });

    $("#submit_rating_3").on('click', function () {
//        $("#user_rating_3").rating('create');
//        alert($("#user_rating").rating('create').val());
//    var input_rating = $("#user_rating_3").rating('create').val()
    var data_dict = {};
    var input_rating = 5;
    data_dict.movie_id = random_movie_id_dict[3];
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
//             alert("it didnt work");
            }
        });
    });

    $("#submit_rating_4").on('click', function () {
//        $("#user_rating_4").rating('create');
//        alert($("#user_rating").rating('create').val());
//    var input_rating = $("#user_rating_4").rating('create').val()
//    console.log(movie_id)
    var data_dict = {};
    var input_rating = 5;
    data_dict.movie_id = random_movie_id_dict[4];
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
//             alert("it didnt work");
            }
        });
    });

    $("#submit_rating_5").on('click', function () {
//        $("#user_rating_5").rating('create');
//        alert($("#user_rating").rating('create').val());
//    var input_rating = $("#user_rating_5").rating('create').val()
//    console.log(movie_id)
    var data_dict = {};
    var input_rating = 5;
    data_dict.movie_id = random_movie_id_dict[5];
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
//             alert("it didnt work");
            }
        });
    });

    $("#submit_rating_6").on('click', function () {
//        $("#user_rating_6").rating('create');
//        alert($("#user_rating").rating('create').val());
//    var input_rating = $("#user_rating_6").rating('create').val()
//    console.log(movie_id)
    var data_dict = {};
    var input_rating = 5;
    data_dict.movie_id = random_movie_id_dict[6];
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
//             alert("it didnt work");
            }
        });
    });

    $("#submit_rating_7").on('click', function () {
//        $("#user_rating_7").rating('create');
//        alert($("#user_rating").rating('create').val());
//    var input_rating = $("#user_rating_7").rating('create').val()
//    console.log(movie_id)
    var data_dict = {};
    var input_rating = 5;
    data_dict.movie_id = random_movie_id_dict[7];
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
//             alert("it didnt work");
            }
        });
    });

    $("#submit_rating_8").on('click', function () {
//        $("#user_rating_8").rating('create');
//        alert($("#user_rating").rating('create').val());
//    var input_rating = $("#user_rating_8").rating('create').val()
//    console.log(movie_id)
    var data_dict = {};
    var input_rating = 5;
    data_dict.movie_id = random_movie_id_dict[8];
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
//             alert("it didnt work");
            }
        });
    });

    $("#submit_rating_9").on('click', function () {
//        $("#user_rating_9").rating('create');
//        alert($("#user_rating").rating('create').val());
//    var input_rating = $("#user_rating_9").rating('create').val()
//    console.log(movie_id)
    var data_dict = {};
    var input_rating = 5;
    data_dict.movie_id = random_movie_id_dict[9];
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
//             alert("it didnt work");
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

$('#rating_form_0').submit(function(e){
    e.preventDefault();
    url = $(this).attr('action');
    data = $(this).serialize();
    $.post(url, data, function(response){
    });
});

$('#rating_form_1').submit(function(e){
    e.preventDefault();
    url = $(this).attr('action');
    data = $(this).serialize();
    $.post(url, data, function(response){
    });
});

$('#rating_form_2').submit(function(e){
    e.preventDefault();
    url = $(this).attr('action');
    data = $(this).serialize();
    $.post(url, data, function(response){
    });
});

$('#rating_form_3').submit(function(e){
    e.preventDefault();
    url = $(this).attr('action');
    data = $(this).serialize();
    $.post(url, data, function(response){
    });
});

$('#rating_form_4').submit(function(e){
    e.preventDefault();
    url = $(this).attr('action');
    data = $(this).serialize();
    $.post(url, data, function(response){
    });
});

$('#rating_form_5').submit(function(e){
    e.preventDefault();
    url = $(this).attr('action');
    data = $(this).serialize();
    $.post(url, data, function(response){
    });
});

$('#rating_form_6').submit(function(e){
    e.preventDefault();
    url = $(this).attr('action');
    data = $(this).serialize();
    $.post(url, data, function(response){
    });
});

$('#rating_form_7').submit(function(e){
    e.preventDefault();
    url = $(this).attr('action');
    data = $(this).serialize();
    $.post(url, data, function(response){
    });
});

$('#rating_form_8').submit(function(e){
    e.preventDefault();
    url = $(this).attr('action');
    data = $(this).serialize();
    $.post(url, data, function(response){
    });
});

$('#rating_form_9').submit(function(e){
    e.preventDefault();
    url = $(this).attr('action');
    data = $(this).serialize();
    $.post(url, data, function(response){
    });
});
