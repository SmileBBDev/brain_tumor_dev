import EncounterListWidget from './EncounterListWidget';

export default function EncounterListPage() {
  return (
    <div className="page">
      <div className="content">
        <EncounterListWidget
          title=""
          size="full"
          showPagination={true}
          showFilters={true}
          showCreateButton={true}
          sortable={true}
        />
      </div>
    </div>
  );
}
