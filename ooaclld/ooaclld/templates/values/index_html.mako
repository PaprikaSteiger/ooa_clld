<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "values" %>
<%block name="title">Values</%block>

<h2>Features</h2>
<p>
    Those are the OOA values
</p>
<div class="clearfix"> </div>
${ctx.render()}
