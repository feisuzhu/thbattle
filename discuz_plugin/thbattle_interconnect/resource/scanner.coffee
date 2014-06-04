msg = (raw_msg) ->
  box = jq '<span class="content">：</span>'
  scanner = ///
  #  [^|]+        # just skip text
    \|(c)[A-Fa-f0-9]{8}
  | \|(s)[12][A-Fa-f0-9]{8}
  | \|([BbIiUurH|RGYW]|[LD]B)
  | \|(\![RGOB])
  ///g

  default_attrib =
    bold: false
    italic: false
    underline: false
    color: null
    shadow: null

  attrib = undefined
  restore = -> attrib = jq.extend true, {}, default_attrib
  restore()

  rgba = (r, g, b, a) ->
    r: r
    g: g
    b: b
    a: a/255.0

  rgba_string = (c) -> "rgba(#{c.r},#{c.g},#{c.b},#{c.a})"

  color = (tok) ->
    attrib.color = rgba (parseInt(tok[i..i+1], 16) for i in [2..8] by 2)...

  shadow = (tok) ->
    attrib.shadow = rgba (parseInt(tok[i..i+1], 16) for i in [3..9] by 2)...
    attrib.shadow.level = parseInt(tok[2])

  ins_text = (text) ->
    if text
      css = {}
      css['font-weight'] = 'bold' if attrib.bold
      css['font-style'] = 'italic' if attrib.italic
      css['text-decoration'] = 'underline' if attrib.underline
      css['color'] = rgba_string(attrib.color) if attrib.color
      css['text-shadow'] = "0 0 #{.3*attrib.shadow.level}em
                            #{rgba_string(attrib.shadow)}" if attrib.shadow
      span = jq '<span></span>'
        .text text
        .css css
      box.append span

  commands =
    c: color
    s: shadow
    B: -> attrib.bold = true
    b: -> attrib.bold = false
    I: -> attrib.italic = true
    i: -> attrib.italic = false
    U: -> attrib.underline = true
    u: -> attrib.underline = false
    H: ->
      color '|c000000ff'
      shadow '|s2000000ff'
    'r': restore
    # shortcuts
    R:  -> color '|cff3535ff'
    G:  -> color '|c208020ff'
    Y:  -> color '|cffff30ff'
    LB: -> color '|c90dce8ff'
    DB: -> color '|c000060ff'
    W:  -> color '|cffffffff'
    '!R': -> color '|cff3535ff'
    '!G': -> color '|c208020ff'
    '!O': -> color '|cffcc77ff'
    '!B': -> color '|c000060ff'

  last = 0
  while (match = scanner.exec raw_msg)
    ins_text(raw_msg[last...match.index])
    last = scanner.lastIndex
    name = null
    for m in match[1..]
      name = name || m
    commands[name](match[0])

  ins_text(raw_msg[last..])

THB.showAyaNews = (data) ->
  jq '#ayanews_content'
    .append jq('<span class="source"></span>').text THB.servers[data[0]]
    .append jq '<span class="tag">『文々。新闻』</span>'
    .append jq('<span class="username"></span>').text data[1]
    .append msg data[2]
    .append jq '<br />'
