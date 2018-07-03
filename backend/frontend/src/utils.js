export async function Q(query, variables) {
  var resp = await fetch('/graphql', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    credentials: 'same-origin',
    body: JSON.stringify({
      query,
      variables: variables || {},
    })
  });
  var text = await resp.text();
  return JSON.parse(text);
}
