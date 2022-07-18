<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "codes" %>
<%block name="title">Codes</%block>
<h2>Featureseets</h2>
<p>
    Those are the OOA Codes
</p>
<div class="clearfix"> </div>
${ctx.render()}
