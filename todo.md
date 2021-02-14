# Commands
- How to run local copy with livereload: `bundle exec jekyll serve --livereload`
- When adding a new plugin: `bundle update` then `bundle install`

# New post checklist
- Make sure post has ok tags
- Make sure images are clickable by changing ![alt text](img path) to [![alt text](img path)](img path)
- Make sure images have OK alt text
- Make sure first paragraph is OK for the excerpt on the main page
- SEO:
    - Make sure post has a descriptive title that is as short as possible
    - Make sure post has a valid description with less than 160 characters
    - Make sure file name doesn't have "and", "to", "for", and etc. words 

# Fixes I've had to do to get this working
- Follow this answer to be able to use livereload: https://stackoverflow.com/a/65547010/2434460
- Had to add `github: [metadata]` to the _config.yml file to suppress that Github API metadata not found message
- Had to remove `relative_permalinks: true` from the _config.yml we get from Hyde
- Had to change "{{ site.baseurl }}assets/css/syntax.css" css filepaths to just "/assets/css/syntax.css", so that they're root relative and it doesn't try loading them from something like "about/assets/css/syntax.css" instead
- Had to hunt the "http://" usages throughout css and html files and replace with just protocol agnostic "//" since the rest of the page is served via https, and having conflicting protocols is problematic