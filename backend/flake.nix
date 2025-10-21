{
  description = "Flake for thbattle backend";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
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
        devShell = pkgs.mkShell {
          buildInputs = [
            pkgs.uv
            (pkgs.python3Minimal.withPackages
              (ps:
                with ps; [
                  redis
                  requests
                  raven
                  gunicorn
                  django
                  graphene
                  django-annoying
                  graphene-django
                  django-redis-sessions
                  itsdangerous
                  msgpack
                  pymysql
                  pyyaml
                  django-schema-graph
                  trueskill
                  qrcode
                  Pillow
                  sentry-sdk
                  pytz
                  psycopg
                  greenlet
                ]))
          ];
        };
      }
    );
}
