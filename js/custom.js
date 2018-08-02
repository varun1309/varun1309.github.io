$( document ).ready(function() {

    animateCircles();
    
    function animateCircles() {

        $("#full-stack-circle").circliful({
            animationStep: 10,
            foregroundBorderWidth: 25,
            backgroundBorderWidth: 25,
            percent: 90,
            textSize: 28,
            textStyle: 'font-size: 12px;',
            textColor: '#666',
        });
        $("#ds-circle").circliful({
            animationStep: 10,
            foregroundBorderWidth: 25,
            backgroundBorderWidth: 25,
            percent: 40,
            textSize: 28,
            textStyle: 'font-size: 12px;',
            textColor: '#666',
        });
        $("#sql-circle").circliful({
            animationStep: 10,
            foregroundBorderWidth: 25,
            backgroundBorderWidth: 25,
            percent: 90,
            textSize: 28,
            textStyle: 'font-size: 12px;',
            textColor: '#666',
        });
        $("#pl-circle").circliful({
            animationStep: 10,
            foregroundBorderWidth: 25,
            backgroundBorderWidth: 25,
            percent: 80,
            textSize: 28,
            textStyle: 'font-size: 12px;',
            textColor: '#666',
        });
        $("#web-circle").circliful({
            animationStep: 10,
            foregroundBorderWidth: 25,
            backgroundBorderWidth: 25,
            percent: 80,
            textSize: 28,
            textStyle: 'font-size: 12px;',
            textColor: '#666',
        });
        $("#web-framework-circle").circliful({
            animationStep: 10,
            foregroundBorderWidth: 25,
            backgroundBorderWidth: 25,
            percent: 90,
            textSize: 28,
            textStyle: 'font-size: 12px;',
            textColor: '#666',
        });
        $("#ds-framework-circle").circliful({
            animationStep: 10,
            foregroundBorderWidth: 25,
            backgroundBorderWidth: 25,
            percent: 30,
            textSize: 28,
            textStyle: 'font-size: 12px;',
            textColor: '#666',
        });
    }

    appearedCount = 0;
    toggle = 0;

    $(document.body).on('disappear', '#Skills', function() {
        console.log('Disappeared');
        appearedCount = appearedCount - 1;
        toggle = 0;
    });

    $(document.body).on('appear', '#Skills', function() {
        console.log('appeared');
        appearedCount = appearedCount + 1;
        if(toggle == 0){
            appearedCount = 1;
            $("#Skills").find(".svg-container").children().remove();
        }
        toggle = 1;
        if(appearedCount == 1){
            animateCircles();
        }
    });

    $('#Skills').appear(function() {
        appearedCount = appearedCount - 1;
    });
});