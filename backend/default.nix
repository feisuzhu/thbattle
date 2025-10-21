{
  lib,
  python3Packages,
}:
python3Packages.buildPythonApplication {
  pname = "thb-backend";
  version = "0.1.0";
  pyproject = true;

  src = ./.;

  buildInputs = [
  ];

  dependencies = with python3Packages; [
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
  ];

  meta = {
    changelog = "";
    description = ''
      Backend for thbattle
    '';
    homepage = "https://github.com/feisuzhu/thbattle";
    license = lib.licenses.gpl3Plus;
    maintainers = with lib.maintainers; [];
  };
}
