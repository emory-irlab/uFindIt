if (!_ma_filt_init) {
  var _ma_filt_init = 1;
  ma_filt_page = function() {
    try {  
      var search_engine = null;
      if (document.location.href.indexOf('google.com/search') >= 0) {
        search_engine = 'google';
        
        var reslist = document.getElementById("ires");
        var iterator = document.evaluate(".//li[@class='g']", reslist, null, XPathResult.UNORDERED_NODE_ITERATOR_TYPE, null );  
      } else if (document.location.href.indexOf('search.yahoo.com/') >= 0) {
        search_engine = 'yahoo';

        var reslist = document.getElementById("web");
        var iterator = document.evaluate(".//li", reslist, null, XPathResult.UNORDERED_NODE_ITERATOR_TYPE, null );  
      } else if (document.location.href.indexOf('bing.com/search') >= 0) {
        search_engine = 'bing';

        var reslist = document.getElementById("results");
        var iterator = document.evaluate(".//li[@class='sa_wr']", reslist, null, XPathResult.UNORDERED_NODE_ITERATOR_TYPE, null );  
      }

      if (search_engine == null) return;

      var elementsToHide = new Array();
      var reselm = iterator.iterateNext();  
      while (reselm) {  
        //if (search_engine != 'yahoo') {
        //  var xp2 = document.evaluate(".//a[starts-with(@href, '/http/answers.yahoo.com/') or starts-with(@href, '/http/wiki.answers.com/') or starts-with(@href, '/http/www.chacha.com/') or starts-with(@href, '/http/answers.google.com/')]", reselm, null, XPathResult.ANY_UNORDERED_NODE_TYPE, null );  
        //} else {
        //  var xp2 = document.evaluate(".//a[starts-with(@href, 'http://answers.yahoo.com/') or starts-with(@href, 'http://wiki.answers.com/') or starts-with(@href, 'http://www.chacha.com/') or starts-with(@href, 'http://answers.google.com/')]", reselm, null, XPathResult.ANY_UNORDERED_NODE_TYPE, null );  
        //}
        //if (xp2.singleNodeValue != null) {
        //  elementsToHide.push(reselm);
        //}
        var h = reselm.innerHTML;
        if (h.indexOf("answers.yahoo.com/") >= 0 
            || h.indexOf("answers.com/") >= 0 
            || h.indexOf("chacha.com/") >= 0 
            || h.indexOf("answers.google.com/") >= 0) 
        {
            elementsToHide.push(reselm);
        }
        reselm = iterator.iterateNext();  
      }   

      for (i=0; i<elementsToHide.length; i++) {
        elementsToHide[i].style.display = "none";
      }
    } catch (e) {  
      //alert(">e>" + e);  
    } 
  }
  ma_filt_page();
}
