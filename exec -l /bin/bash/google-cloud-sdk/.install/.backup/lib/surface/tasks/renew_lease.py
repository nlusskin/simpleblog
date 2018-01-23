# Copyright 2017 Google Inc. All Rights Reserved.
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
"""`gcloud tasks renew-lease` command."""

from googlecloudsdk.api_lib.tasks import tasks
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.tasks import flags
from googlecloudsdk.command_lib.tasks import parsers


class RenewLease(base.Command):
  """Renew the lease on a task in a pull queue."""

  @staticmethod
  def Args(parser):
    flags.AddTaskResourceArgs(parser, 'to renew the lease of')
    flags.AddLocationFlag(parser)
    flags.AddTaskLeaseScheduleTimeFlag(parser, 'renewing')
    flags.AddTaskLeaseDurationFlag(parser)

  def Run(self, args):
    tasks_client = tasks.Tasks()
    queue_ref = parsers.ParseQueue(args.queue, args.location)
    task_ref = parsers.ParseTask(args.task, queue_ref)
    duration = parsers.FormatLeaseDuration(args.lease_duration)
    return tasks_client.RenewLease(task_ref, args.schedule_time, duration)
