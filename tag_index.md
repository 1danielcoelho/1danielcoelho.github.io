---
layout: page
title: Tag index
---

Browse all posts by tag

{%- assign date_format = site.minima.date_format | default: "%b %-d, %Y" -%}
{% for tag in site.tags %}

  <h3 id="{{ tag[0] }}" class="post-tag post-tag-title">{{ tag[0] }}</h3>  
  <ul>
    {% for post in tag[1] %}
      <li>
          <a href="{{ post.url }}">{{ post.title }}</a>
          
          &nbsp;

          <small>
              <a class="post-date" href="/archive#{{ post.date | date: '%B %Y' }}">
                  {{ post.date | date: date_format }}
              </a>  
          </small>
      </li>
    {% endfor %}
  </ul>
{% endfor %}
