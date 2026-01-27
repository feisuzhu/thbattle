{
  description = "Flake for thbattle backend";

  inputs = {
    nixpkgs.url = "flake:nixpkgs";
    systems.url = "github:nix-systems/default";
  };

  outputs = {
    nixpkgs,
    systems,
    ...
  }: let
    eachSystem = nixpkgs.lib.genAttrs (import systems);
    pkgsFor = nixpkgs.legacyPackages;
  in {
    devShells = eachSystem (system: let
      pkgs = pkgsFor.${system};
    in {
      default = pkgs.mkShell {
        name = "thb-backend-shell";
        packages = [
          pkgs.python3
          pkgs.python3Packages.uv
        ];

        env.SECRET_KEY = "ew&(_dc#t346(!qzan_paw2^5f3r)3g80)1l+s_e%7&!a7nr$-";
      };
    });
  };
}
