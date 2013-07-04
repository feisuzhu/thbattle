var THBViewer = angular.module("thbviewer", ['ui.bootstrap', 'thbviewer.ui']);

THBViewer.config(function($routeProvider) {
    $routeProvider.
        when("/Cards", {controller: CardListController, templateUrl: "templates/cardlist.html"}).
        when("/Characters", {controller: CharacterListController, templateUrl: "templates/charlist.html"}).
        when("/Modes", {controller: ModeListController, templateUrl: "templates/modelist.html"}).
        otherwise({redirectTo: "Cards"});
});


THBViewer.constant("options", {
    resourceUrl: "http://update.thbattle.net/src/gamepack/thb/ui/res",
    dataUrl: "/thbviewer.json"
});


THBViewer.service("thbData", function($http, options) {
    this.findByToken = function(lst, token) {
        for(k in lst) {
            if(lst[k].token === token) return lst[k];
        }
    };

    this.getDefinition = function() {
        return $http.get(options.dataUrl, {cache: true}); 
    };
});


THBViewer.run(function($rootScope, options) {
    $rootScope.options = options;
});
