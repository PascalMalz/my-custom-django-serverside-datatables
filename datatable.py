from collections import namedtuple
import operator
from django.db.models import Q
from functools import reduce

order_dict = {'asc': '', 'desc': '-'}


class DataTablesServer(object):
    def __init__(self, request, columns, qs):
        print("Starting columns: ",columns)

        
        # values specified by the datatable for filtering, sorting, paging
        print("Starting request.GET: ",request.GET)
        self.request_values = request.GET

        self.columns = self.request_values['sColumns'].split(",")
        print('self.columns: ',self.columns)

        # results from the db
        print("Starting result_data")
        self.result_data = None
        # total in the table after filtering
        print("Starting cardinality_filtered")
        self.cardinality_filtered = 0
        # total in the table unfiltered
        
        self.cardinality = 0
        print("Starting  request.user")
        self.user = request.user
        print("Starting qs")
        self.qs = qs
        print("Starting run_queries")
        self.run_queries()
        print("Finished run_queries")

    def output_result(self):
        output = dict()
        output['sEcho'] = str(int(self.request_values['sEcho']))
        output['iTotalRecords'] = str(self.qs.count())
        output['iTotalDisplayRecords'] = str(self.cardinality_filtered)
        data_rows = []

        for row in self.result_data:
            data_row = []
            for i in range(len(self.columns)):
                # val = getattr(row, self.columns[i])
                val = row[self.columns[i]]
                data_row.append(val)
            data_rows.append(data_row)
        output['aaData'] = data_rows
        return output

    def run_queries(self):
        # pages has 'start' and 'length' attributes
        pages = self.paging()
        # the term you entered into the datatable search
        _filter = self.filtering()
        # the document field you chose to sort
        sorting = self.sorting()
        # custom filter
        qs = self.qs

        if _filter:
            if (_filter[1] == 'or'):
                _filter = _filter[0]
                data = qs.filter(
                reduce(operator.or_, _filter)).order_by('%s' % sorting)
            elif (_filter[1] == 'and'):
                _filter = _filter[0]
                data = qs.filter(
                reduce(operator.and_, _filter)).order_by('%s' % sorting)
            
            
            len_data = data.count()
            data = list(data[pages.start:pages.length].values(*self.columns))
        else:
            data = qs.order_by('%s' % sorting).values(*self.columns)
            len_data = data.count()
            _index = int(pages.start)
            data = data[_index:_index + (pages.length - pages.start)]

        self.result_data = list(data)

        # length of filtered set
        if _filter:
            self.cardinality_filtered = len_data
        else:
            self.cardinality_filtered = len_data
        self.cardinality = pages.length - pages.start

    def filtering(self):
        # build your filter spec
        or_filter = []
        culomn_filters = []
        q_list = []
        if (self.request_values['sSearch'] == ""):
            for possibleFilter in self.request_values:
                print('possibleFilter[8:]',possibleFilter[8:])
                if (possibleFilter[:8] == 'sSearch_'):
                    print('self.request_values[\'sSearch\'+str(possibleFilter[7:])] ','sSearch'+str(possibleFilter[7:]))
                    print(self.request_values['sSearch'+str(possibleFilter[7:])])
                    if (self.request_values['sSearch'+str(possibleFilter[7:])] != ""):
                        print('colum_filter_value: ',self.request_values[possibleFilter])
                        culomn_filters.append((self.columns[int(possibleFilter[8:])]+'__icontains', self.request_values['sSearch'+str(possibleFilter[7:])].replace("(","").replace(")","")))
            if (culomn_filters):
                q_list = [[Q(x) for x in culomn_filters], 'and']
        print('culomn_filters: ',culomn_filters)
        
        if (self.request_values.get('sSearch')) and (self.request_values['sSearch'] != ""):
            for i in range(len(self.columns)):
                or_filter.append((self.columns[i]+'__icontains', self.request_values['sSearch']))
            q_list = [[Q(x) for x in or_filter], 'or']
        print('or_filter: ', or_filter)

                
        
        print(q_list)
        return q_list

    def sorting(self):

        order = ''
        if (self.request_values['iSortCol_0'] != "") and (int(self.request_values['iSortingCols']) > 0):

            for i in range(int(self.request_values['iSortingCols'])):
                # column number
                column_number = int(self.request_values['iSortCol_' + str(i)])
                # sort direction
                sort_direction = self.request_values['sSortDir_' + str(i)]

                order = ('' if order == '' else ',') +order_dict[sort_direction]+self.columns[column_number]

        return order

    def paging(self):

        pages = namedtuple('pages', ['start', 'length'])

        if (self.request_values['iDisplayStart'] != "") and (self.request_values['iDisplayLength'] != -1):
            pages.start = int(self.request_values['iDisplayStart'])
            pages.length = pages.start + int(self.request_values['iDisplayLength'])

        return pages