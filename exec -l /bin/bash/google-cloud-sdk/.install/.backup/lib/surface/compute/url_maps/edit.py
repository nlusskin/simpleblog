# Copyright 2014 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Command for modifying URL maps."""

import cStringIO

from apitools.base.protorpclite import messages
from apitools.base.py import encoding

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import property_selector
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.url_maps import flags
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import edit

import yaml


class InvalidResourceError(exceptions.ToolException):
  # Normally we'd want to subclass core.exceptions.Error, but base_classes.Edit
  # abuses ToolException to classify errors when displaying messages to users,
  # and we should continue to fit in that framework for now.
  pass


@base.ReleaseTracks(base.ReleaseTrack.GA)
class EditGA(base.Command):
  """Modify URL maps."""

  DEFAULT_FORMAT = 'yaml'
  URL_MAP_ARG = None
  TRACK = 'v1'

  @classmethod
  def Args(cls, parser):
    cls.URL_MAP_ARG = flags.UrlMapArgument()
    cls.URL_MAP_ARG.AddArgument(parser)

  def _ProcessEditedResource(self, holder, url_map_ref, file_contents,
                             original_object, original_record,
                             modifiable_record, args):
    """Returns an updated resource that was edited by the user."""

    # It's very important that we replace the characters of comment
    # lines with spaces instead of removing the comment lines
    # entirely. JSON and YAML deserialization give error messages
    # containing line, column, and the character offset of where the
    # error occurred. If the deserialization fails; we want to make
    # sure those numbers map back to what the user actually had in
    # front of him or her otherwise the errors will not be very
    # useful.
    non_comment_lines = '\n'.join(
        ' ' * len(line) if line.startswith('#') else line
        for line in file_contents.splitlines())

    modified_record = base_classes.DeserializeValue(
        non_comment_lines, args.format or EditGA.DEFAULT_FORMAT)

    # Normalizes all of the fields that refer to other
    # resource. (i.e., translates short names to URIs)
    reference_normalizer = property_selector.PropertySelector(
        transformations=self.GetReferenceNormalizers(holder.resources))
    modified_record = reference_normalizer.Apply(modified_record)

    if modifiable_record == modified_record:
      new_object = None

    else:
      modified_record['name'] = original_record['name']
      fingerprint = original_record.get('fingerprint')
      if fingerprint:
        modified_record['fingerprint'] = fingerprint

      new_object = encoding.DictToMessage(
          modified_record, holder.client.messages.UrlMap)

    # If existing object is equal to the proposed object or if
    # there is no new object, then there is no work to be done, so we
    # return the original object.
    if not new_object or original_object == new_object:
      return [original_object]

    return holder.client.MakeRequests(
        [self.GetSetRequest(holder.client, url_map_ref, new_object)])

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    url_map_ref = self.URL_MAP_ARG.ResolveAsResource(args, holder.resources)
    get_request = self.GetGetRequest(client, url_map_ref)

    objects = client.MakeRequests([get_request])

    resource_list = self.EditResource(args, client, holder, objects[0],
                                      url_map_ref)

    for resource in resource_list:
      yield resource

  def EditResource(self, args, client, holder, original_object, url_map_ref):
    original_record = encoding.MessageToDict(original_object)

    # Selects only the fields that can be modified.
    field_selector = property_selector.PropertySelector(properties=[
        'defaultService',
        'description',
        'hostRules',
        'pathMatchers',
        'tests',
    ])
    modifiable_record = field_selector.Apply(original_record)

    buf = self.BuildFileContents(args, client, modifiable_record,
                                 original_record)
    file_contents = buf.getvalue()
    while True:
      try:
        file_contents = edit.OnlineEdit(file_contents)
      except edit.NoSaveException:
        raise exceptions.ToolException('Edit aborted by user.')
      try:
        resource_list = self._ProcessEditedResource(
            holder, url_map_ref, file_contents, original_object,
            original_record, modifiable_record, args)
        break
      except (ValueError, yaml.error.YAMLError,
              messages.ValidationError,
              exceptions.ToolException) as e:
        if isinstance(e, ValueError):
          message = e.message
        else:
          message = str(e)

        if isinstance(e, exceptions.ToolException):
          problem_type = 'applying'
        else:
          problem_type = 'parsing'

        message = ('There was a problem {0} your changes: {1}'
                   .format(problem_type, message))
        if not console_io.PromptContinue(
            message=message,
            prompt_string='Would you like to edit the resource again?'):
          raise exceptions.ToolException('Edit aborted by user.')
    return resource_list

  def BuildFileContents(self, args, client, modifiable_record, original_record):
    buf = cStringIO.StringIO()
    for line in base_classes.HELP.splitlines():
      buf.write('#')
      if line:
        buf.write(' ')
      buf.write(line)
      buf.write('\n')
    buf.write('\n')
    buf.write(base_classes.SerializeDict(modifiable_record,
                                         args.format or EditGA.DEFAULT_FORMAT))
    buf.write('\n')
    example = base_classes.SerializeDict(
        encoding.MessageToDict(self.GetExampleResource(client)),
        args.format or EditGA.DEFAULT_FORMAT)
    base_classes.WriteResourceInCommentBlock(example, 'Example resource:', buf)
    buf.write('#\n')
    original = base_classes.SerializeDict(original_record,
                                          args.format or EditGA.DEFAULT_FORMAT)
    base_classes.WriteResourceInCommentBlock(original, 'Original resource:',
                                             buf)
    return buf

  def GetExampleResource(self, client):
    backend_service_uri_prefix = (
        'https://www.googleapis.com/compute/%(track)s/projects/'
        'my-project/global/backendServices/' % {
            'track': self.TRACK
        })
    backend_bucket_uri_prefix = (
        'https://www.googleapis.com/compute/%(track)s/projects/'
        'my-project/global/backendBuckets/' % {
            'track': self.TRACK
        })
    return client.messages.UrlMap(
        name='site-map',
        defaultService=backend_service_uri_prefix + 'default-service',
        hostRules=[
            client.messages.HostRule(
                hosts=['*.google.com', 'google.com'], pathMatcher='www'),
            client.messages.HostRule(
                hosts=['*.youtube.com', 'youtube.com', '*-youtube.com'],
                pathMatcher='youtube'),
        ],
        pathMatchers=[
            client.messages.PathMatcher(
                name='www',
                defaultService=backend_service_uri_prefix + 'www-default',
                pathRules=[
                    client.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=backend_service_uri_prefix + 'search'),
                    client.messages.PathRule(
                        paths=['/search/ads', '/search/ads/*'],
                        service=backend_service_uri_prefix + 'ads'),
                    client.messages.PathRule(
                        paths=['/images/*'],
                        service=backend_bucket_uri_prefix + 'images'),
                ]),
            client.messages.PathMatcher(
                name='youtube',
                defaultService=backend_service_uri_prefix + 'youtube-default',
                pathRules=[
                    client.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=backend_service_uri_prefix + 'youtube-search'),
                    client.messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=backend_service_uri_prefix + 'youtube-watch'),
                ]),
        ],
        tests=[
            client.messages.UrlMapTest(
                host='www.google.com',
                path='/search/ads/inline?q=flowers',
                service=backend_service_uri_prefix + 'ads'),
            client.messages.UrlMapTest(
                host='youtube.com',
                path='/watch/this',
                service=backend_service_uri_prefix + 'youtube-default'),
            client.messages.UrlMapTest(
                host='youtube.com',
                path='/images/logo.png',
                service=backend_bucket_uri_prefix + 'images'),
        ])

  def GetReferenceNormalizers(self, resource_registry):

    def MakeReferenceNormalizer(field_name, allowed_collections):
      """Returns a function to normalize resource references."""
      def NormalizeReference(reference):
        """Returns normalized URI for field_name."""
        try:
          value_ref = resource_registry.Parse(reference)
        except resources.UnknownCollectionException:
          raise InvalidResourceError(
              '[{field_name}] must be referenced using URIs.'.format(
                  field_name=field_name))

        if value_ref.Collection() not in allowed_collections:
          raise InvalidResourceError(
              'Invalid [{field_name}] reference: [{value}].'. format(
                  field_name=field_name, value=reference))
        return value_ref.SelfLink()
      return NormalizeReference

    allowed_collections = ['compute.backendServices', 'compute.backendBuckets']
    return [
        ('defaultService', MakeReferenceNormalizer(
            'defaultService', allowed_collections)),
        ('pathMatchers[].defaultService', MakeReferenceNormalizer(
            'defaultService', allowed_collections)),
        ('pathMatchers[].pathRules[].service', MakeReferenceNormalizer(
            'service', allowed_collections)),
        ('tests[].service', MakeReferenceNormalizer(
            'service', allowed_collections)),
    ]

  def GetGetRequest(self, client, url_map_ref):
    return (client.apitools_client.urlMaps, 'Get',
            client.messages.ComputeUrlMapsGetRequest(**url_map_ref.AsDict()))

  def GetSetRequest(self, client, url_map_ref, replacement):
    return (client.apitools_client.urlMaps, 'Update',
            client.messages.ComputeUrlMapsUpdateRequest(
                urlMapResource=replacement, **url_map_ref.AsDict()))


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class EditBeta(EditGA):
  """Modify URL maps."""

  TRACK = 'beta'


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class EditAlpha(EditBeta):
  """Modify URL maps."""

  TRACK = 'alpha'


EditGA.detailed_help = {
    'brief': 'Modify URL maps',
    'DESCRIPTION': """\
        *{command}* can be used to modify a URL map. The URL map
        resource is fetched from the server and presented in a text
        editor. After the file is saved and closed, this command will
        update the resource. Only fields that can be modified are
        displayed in the editor.

        The editor used to modify the resource is chosen by inspecting
        the ``EDITOR'' environment variable.
        """,
}
EditBeta.detailed_help = EditGA.detailed_help
EditAlpha.detailed_help = EditBeta.detailed_help
