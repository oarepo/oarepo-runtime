from oarepo import __version__ as oarepo_version

# compatibility setting between invenio rdm 11 and invenio rdm 12
# can be removed when invenio rdm 11 is no longer supported
if oarepo_version.split('.')[0] == "11":
    from flask_babelex import lazy_gettext
else:
    from flask_babel import lazy_gettext

__all__ = ('lazy_gettext', )