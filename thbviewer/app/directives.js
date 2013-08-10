var popoverFactory = function(varname, attrib, template) {
  return function(thbData) {
    return {
      restrict: 'EA',
      replace: true,
      scope: { title: '@', content: '@', placement: '@', animation: '&', isOpen: '&' },
      templateUrl: 'templates/' + template + '.html',
      controller: function($scope, $element, $attrs) {
        $scope.times = function(n) {
            return new Array(n);
        };
        $attrs.$observe('content', function(v) {
          thbData.getDefinition().success(function(data) {
            $scope[varname] = thbData.findByToken(data[attrib], v);
          });
        });
      }
    };
  }
};

angular.module('thbviewer.ui', ['ui.bootstrap.tooltip'])

.directive('cardpopoverPopup', popoverFactory('card', 'Cards', 'cardpopover'))
.directive('cardpopover', function ($tooltip) {
  return $tooltip('cardpopover', 'cardpopover', 'click');
})

.directive('charpopoverPopup', popoverFactory('character', 'Characters', 'charpopover'))
.directive('charpopover', function ($tooltip) {
  return $tooltip('charpopover', 'charpopover', 'click');
})

.directive('modepopoverPopup', popoverFactory('mode', 'Modes', 'modepopover'))
.directive('modepopover', function ($tooltip) {
  return $tooltip('modepopover', 'modepopover', 'click');
});
