jQuery(document).ready(function(){
    var cookieBarNotification = jQuery('.js-cookie-bar-notification'),
        acceptButton = jQuery('.js-button-accept'),
        optOutButton = jQuery('.js-button-optout');

    function createCookie(key, value, expiresDays) {

        var currentDate = new Date();

        currentDate.setTime(currentDate.getTime() + (expiresDays * 24 * 60 * 60 * 1000));
        var expires = 'expires=' + currentDate.toUTCString(),
            cookie = escape(key) + '=' + escape(value) + '; Path=/;' + expires;

        document.cookie = cookie;

    }

    function readCookie (name) {

        var key = name + '=',
            cookies = document.cookie.split(';');

        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i];
            while (cookie.charAt(0) === ' ') {
                cookie = cookie.substring(1, cookie.length);
            }
            if (cookie.indexOf(key) === 0) {
                return cookie.substring(key.length, cookie.length);
            }
        }

        return null;

    }

    switch (readCookie('cookie_consent_status')) {
        case 'true' :
            //cookieBarNotification.fadeOut(1000);
        break;
        case null:
            cookieBarNotification.fadeIn(1200);
            acceptButton.on('click', function () {
                cookieBarNotification.fadeOut(1000);
                createCookie('cookie_consent_status', true, 30);
            });
            if(optOutButton.length > 0) {
                optOutButton.on('click', function () {
                    cookieBarNotification.fadeOut(1000);
                    createCookie('cookie_consent_status', true, 30);
                });
            }
        break;
        default:
            cookieBarNotification.fadeIn();
    }
});
