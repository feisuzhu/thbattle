{
  description = "Flake for thbattle backend";

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
            name = "thb-backend-shell";
            packages = [
              pkgs.python3
              pkgs.python3Packages.uv
            ];
            shellHook = ''
              export SECRET_KEY='ew&(_dc#t346(!qzan_paw2^5f3r)3g80)1l+s_e%7&!a7nr$-'
            '';
          };
        };
      }
    );
}
