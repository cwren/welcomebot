# Release Process

```
uv run pytest
uv version --bump patch
version=$(uv version --short)
tag=v$version
git commit -S -a -m "publishing $tag"
git tag -m "publishing $tag" $tag
git push github
git push github tag $tag 
```