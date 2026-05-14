{{ fullname | escape | underline}}

.. automodule:: {{ fullname }}

{% block functions %}
{% if functions %}
.. rubric:: Functions

.. autosummary::
   :toctree: .
   :nosignatures:

{% for item in functions %}
   {{ item }}
{%- endfor %}
{% endif %}
{% endblock %}

{% block classes %}
{% if classes %}
.. rubric:: Classes

.. autosummary::
   :toctree: .
   :nosignatures:

{% for item in classes %}
   {{ item }}
{%- endfor %}
{% endif %}
{% endblock %}