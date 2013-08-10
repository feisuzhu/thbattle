var MainController = function($scope, $location) {
    $scope.links = [
        {href: "#/Cards", title: "卡牌"},
        {href: "#/Characters", title: "角色"},
        {href: "#/Modes", title: "游戏模式"},
    ];

    $scope.isCurrent = function(url) {
        return url.slice(1) === $location.$$url;
    };
};


var ListControllerFactory = function(fortype) {
    return function($scope, thbData) {
        $scope.items = [];
        thbData.getDefinition().success(function(data) {
            $scope.items = data[fortype];
        });
    };
}

var CardListController = ListControllerFactory('Cards');
var CharacterListController = ListControllerFactory('Characters');
var ModeListController = ListControllerFactory('Modes');
