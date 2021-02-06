---
layout: page
title: Archive
---

Browse all posts by month and year

{% assign postsByYearMonth = site.posts | group_by_exp: "post", "post.date | date: '%B %Y'" %}
{% for yearMonth in postsByYearMonth %}

<h3 id="{{ yearMonth.name }}">{{ yearMonth.name }}</h3>
<ul>
  {% for post in yearMonth.items %}
    <li>
        <a href="{{ post.url }}">{{ post.title }}</a>

        &nbsp;

        {%- for tag in post.tags -%}
            <small>
                <a class="post-tag" href="/tag_index#{{tag}}">
                    {{ tag }}
                </a>
            </small>
        {%- endfor -%}
    </li>

{% endfor %}

</ul>
{% endfor %}
