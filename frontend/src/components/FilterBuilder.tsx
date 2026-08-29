'use client';

import { useState } from 'react';
import { Plus, Trash2, Save, Play, X } from 'lucide-react';
import { filtersAPI } from '@/lib/api';
import toast from 'react-hot-toast';

interface FilterCondition {
  field: string;
  operator: string;
  value: string;
  value2?: string;
}

interface FilterGroup {
  logic: 'AND' | 'OR';
  conditions: FilterCondition[];
}

interface FilterBuilderProps {
  onApply: (config: any) => void;
  savedFilters: any[];
  onLoadSaved: (filterId: string) => void;
}

const FIELDS = [
  { value: 'full_name', label: 'Full Name' },
  { value: 'email', label: 'Email' },
  { value: 'phone', label: 'Phone' },
  { value: 'city', label: 'City' },
  { value: 'department_tag', label: 'Department' },
  { value: 'career_level', label: 'Career Level' },
  { value: 'employment_type', label: 'Employment Type' },
  { value: 'source_channel', label: 'Source Channel' },
  { value: 'applied_designation', label: 'Designation' },
  { value: 'tags', label: 'Tags' },
];

const OPERATORS = [
  { value: 'equals', label: 'Equals' },
  { value: 'not_equals', label: 'Not Equals' },
  { value: 'contains', label: 'Contains' },
  { value: 'starts_with', label: 'Starts With' },
  { value: 'gt', label: 'Greater Than' },
  { value: 'lt', label: 'Less Than' },
  { value: 'between', label: 'Between' },
  { value: 'in_list', label: 'In List' },
  { value: 'is_empty', label: 'Is Empty' },
];

export default function FilterBuilder({ onApply, savedFilters, onLoadSaved }: FilterBuilderProps) {
  const [groups, setGroups] = useState<FilterGroup[]>([
    { logic: 'AND', conditions: [{ field: 'full_name', operator: 'contains', value: '' }] }
  ]);
  const [joinLogic, setJoinLogic] = useState<'AND' | 'OR'>('OR');
  const [filterName, setFilterName] = useState('');
  const [showSave, setShowSave] = useState(false);

  const addGroup = () => {
    setGroups([...groups, { logic: 'AND', conditions: [{ field: 'full_name', operator: 'contains', value: '' }] }]);
  };

  const removeGroup = (idx: number) => {
    setGroups(groups.filter((_, i) => i !== idx));
  };

  const addCondition = (groupIdx: number) => {
    const newGroups = [...groups];
    newGroups[groupIdx].conditions.push({ field: 'full_name', operator: 'contains', value: '' });
    setGroups(newGroups);
  };

  const removeCondition = (groupIdx: number, condIdx: number) => {
    const newGroups = [...groups];
    newGroups[groupIdx].conditions = newGroups[groupIdx].conditions.filter((_, i) => i !== condIdx);
    setGroups(newGroups);
  };

  const updateCondition = (groupIdx: number, condIdx: number, key: keyof FilterCondition, val: string) => {
    const newGroups = [...groups];
    (newGroups[groupIdx].conditions[condIdx] as any)[key] = val;
    setGroups(newGroups);
  };

  const updateGroupLogic = (groupIdx: number, logic: 'AND' | 'OR') => {
    const newGroups = [...groups];
    newGroups[groupIdx].logic = logic;
    setGroups(newGroups);
  };

  const buildConfig = () => ({
    groups: groups.map((g) => ({
      logic: g.logic,
      conditions: g.conditions.filter((c) => c.value !== '' || c.operator === 'is_empty'),
    })).filter((g) => g.conditions.length > 0),
    join_logic: joinLogic,
  });

  const handleApply = () => {
    const config = buildConfig();
    if (config.groups.length === 0) {
      toast.error('Add at least one filter condition');
      return;
    }
    onApply(config);
  };

  const handleSave = async () => {
    if (!filterName.trim()) {
      toast.error('Enter a filter name');
      return;
    }
    try {
      await filtersAPI.save({ name: filterName, scope: 'personal', filter_config: buildConfig() });
      toast.success('Filter saved');
      setShowSave(false);
      setFilterName('');
    } catch {
      toast.error('Failed to save filter');
    }
  };

  return (
    <div className="space-y-4">
      {/* Saved Filters */}
      {savedFilters.length > 0 && (
        <div className="flex flex-wrap gap-2">
          <span className="text-xs text-slate-500 font-medium self-center">Saved:</span>
          {savedFilters.map((f) => (
            <button
              key={f.filter_id}
              onClick={() => onLoadSaved(f.filter_id)}
              className="filter-chip filter-chip-inactive hover:bg-blue-50 hover:text-blue-700 hover:border-blue-300"
            >
              {f.name}
            </button>
          ))}
        </div>
      )}

      {/* Filter Groups */}
      {groups.map((group, gIdx) => (
        <div key={gIdx} className="bg-slate-50 rounded-lg p-4 border border-slate-200">
          <div className="flex items-center gap-3 mb-3">
            {gIdx > 0 && (
              <div className="flex items-center gap-1">
                <select
                  value={joinLogic}
                  onChange={(e) => setJoinLogic(e.target.value as 'AND' | 'OR')}
                  className="px-2 py-1 bg-white border border-blue-300 text-blue-700 rounded text-xs font-bold"
                >
                  <option value="OR">OR</option>
                  <option value="AND">AND</option>
                </select>
              </div>
            )}
            <span className="text-xs font-medium text-slate-500">Group {gIdx + 1}</span>
            {groups.length > 1 && (
              <button onClick={() => removeGroup(gIdx)} className="p-1 hover:bg-red-100 rounded text-red-500">
                <Trash2 className="w-3 h-3" />
              </button>
            )}
          </div>

          <div className="space-y-2">
            {group.conditions.map((cond, cIdx) => (
              <div key={cIdx} className="flex items-center gap-2 flex-wrap">
                {cIdx > 0 && (
                  <select
                    value={group.logic}
                    onChange={(e) => updateGroupLogic(gIdx, e.target.value as 'AND' | 'OR')}
                    className="px-2 py-1.5 bg-white border border-slate-200 rounded text-xs font-bold text-blue-600"
                  >
                    <option value="AND">AND</option>
                    <option value="OR">OR</option>
                  </select>
                )}

                <select
                  value={cond.field}
                  onChange={(e) => updateCondition(gIdx, cIdx, 'field', e.target.value)}
                  className="px-2 py-1.5 bg-white border border-slate-200 rounded text-xs"
                >
                  {FIELDS.map((f) => (
                    <option key={f.value} value={f.value}>{f.label}</option>
                  ))}
                </select>

                <select
                  value={cond.operator}
                  onChange={(e) => updateCondition(gIdx, cIdx, 'operator', e.target.value)}
                  className="px-2 py-1.5 bg-white border border-slate-200 rounded text-xs"
                >
                  {OPERATORS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>

                {cond.operator !== 'is_empty' && (
                  <input
                    type="text"
                    value={cond.value}
                    onChange={(e) => updateCondition(gIdx, cIdx, 'value', e.target.value)}
                    placeholder="Value"
                    className="px-3 py-1.5 bg-white border border-slate-200 rounded text-xs flex-1 min-w-[120px]"
                  />
                )}

                {cond.operator === 'between' && (
                  <input
                    type="text"
                    value={cond.value2 || ''}
                    onChange={(e) => updateCondition(gIdx, cIdx, 'value2', e.target.value)}
                    placeholder="And"
                    className="px-3 py-1.5 bg-white border border-slate-200 rounded text-xs w-24"
                  />
                )}

                {group.conditions.length > 1 && (
                  <button onClick={() => removeCondition(gIdx, cIdx)} className="p-1 hover:bg-red-100 rounded text-red-400">
                    <X className="w-3 h-3" />
                  </button>
                )}
              </div>
            ))}
          </div>

          <button
            onClick={() => addCondition(gIdx)}
            className="mt-2 flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 font-medium"
          >
            <Plus className="w-3 h-3" /> Add Condition
          </button>
        </div>
      ))}

      {/* Actions */}
      <div className="flex items-center gap-3">
        <button
          onClick={addGroup}
          className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50"
        >
          <Plus className="w-3 h-3" /> Add Group
        </button>

        <button
          onClick={handleApply}
          className="flex items-center gap-1 px-4 py-1.5 bg-blue-600 text-white text-xs font-medium rounded-lg hover:bg-blue-700"
        >
          <Play className="w-3 h-3" /> Apply Filter
        </button>

        <button
          onClick={() => setShowSave(!showSave)}
          className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50"
        >
          <Save className="w-3 h-3" /> Save Filter
        </button>
      </div>

      {showSave && (
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={filterName}
            onChange={(e) => setFilterName(e.target.value)}
            placeholder="Filter name, e.g. Senior Engineers Dubai"
            className="px-3 py-1.5 border border-slate-200 rounded text-sm flex-1 max-w-xs"
          />
          <button
            onClick={handleSave}
            className="px-3 py-1.5 bg-green-600 text-white text-xs font-medium rounded-lg hover:bg-green-700"
          >
            Save
          </button>
        </div>
      )}
    </div>
  );
}
