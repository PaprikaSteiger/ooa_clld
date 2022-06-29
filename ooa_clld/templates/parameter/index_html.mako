<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "parameters" %>
<%block name="title">Features</%block>

<h2>Features</h2>
<p>
    Those are the OOA parameters
    ##A feature is a structural property of language that describes one aspect of cross-linguistic
    ##diversity. A WALS feature has between 2 and 28 different values, shown by different colours
    ##on the maps. Most features correspond straightforwardly to chapters, but some chapters are
    ##about multiple features.
</p>
${type(ctx)}
<div class="clearfix"> </div>
${ctx.render()}

<script type="text/javascript">
    ## $(document).ready(function() {
    ##    $("#${ms.eid}").on("select2-selecting", function(e) {
    ##        document.location.href = '${ms.url}?id=' + e.val;
    ##    });
    ##});
</script>