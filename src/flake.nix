{
  description = "A Sanguosha board game clone, based on Touhou Project";

  inputs = {
    nixpkgs.url = "flake:nixpkgs";
    utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    nixpkgs,
    utils,
    ...
  }:
    utils.lib.eachDefaultSystem (
      system: let
        pkgs = nixpkgs.legacyPackages.${system};
      in {
        devShells = {
          default = pkgs.mkShell {
            name = "thbattle-shell";
            packages = [
              pkgs.python3
              pkgs.python3Packages.uv
            ];
          };
        };
      }
    );
}
